import os
import json
from urllib.parse import urlparse

from flask import Flask, request, Response, send_from_directory
from github import Github
from waitress import serve

app = Flask(__name__)


@app.route('/analyze', methods=['GET'])
def analyze():
  # Extract the URL and FOLDER parameters from the request data
  url = request.args.get('url')
  folder = request.args.get('folder')

  # Set the API key
  api_key = os.environ['GIT_API_KEY']

  # Parse the URL
  url = urlparse(url)
  path_parts = url.path.split('/')
  repo = '/'.join(path_parts[1:3])
  pr_or_commit = path_parts[3]
  number_or_hash = path_parts[4]

  # Create a Github instance
  g = Github(api_key)

  # Fetch data from GitHub API
  if pr_or_commit == 'pull':
    pr = g.get_repo(repo).get_pull(int(number_or_hash))
    files = []
    for f in pr.get_files():
      if (not folder) or (folder and folder.lower() in f.filename.lower()):
        if any(
            ext in f.filename.lower()
            for ext in ['.java', '.js', '.cpp', '.rb', '.py', '.scala', '.cc', '.groovy', '.jsp', '.kt'
                        ]) and 'test' not in f.filename.lower():
          try:
            file_content = g.get_repo(repo).get_contents(
                f.filename,
                ref=pr.get_commits().reversed[0].sha).decoded_content.decode(
                    'utf-8')
            files.append({
                'address': f.filename,
                'patch': f.patch,
                'raw': file_content
            })
          except Exception as e:
            files.append({
                'address': f.filename,
                'patch': f.patch,
                'raw': f'Error getting file content: {str(e)}'
            })
    data = {
        'title': pr.title,
        'hash': pr.get_commits().reversed[0].sha,
        'files': files
    }
  elif pr_or_commit == 'commit':
    commit = g.get_repo(repo).get_commit(number_or_hash)
    files = []
    for f in commit.files:
      if (not folder) or (folder and folder.lower() in f.filename.lower()):
        if any(
            ext in f.filename.lower()
            for ext in ['.java', '.js', '.cpp', '.rb', '.py', '.scala', '.cc', '.groovy', '.jsp', '.kt'
                        ]) and 'test' not in f.filename.lower():
          try:
            file_content = g.get_repo(repo).get_contents(
                f.filename, ref=commit.sha).decoded_content.decode('utf-8')
            files.append({
                'address': f.filename,
                'patch': f.patch,
                'raw': file_content
            })
          except Exception as e:
            files.append({
                'address': f.filename,
                'patch': f.patch,
                'raw': f'Error getting file content: {str(e)}'
            })
    data = {
        'message': commit.commit.message,
        'hash': commit.sha,
        'files': files
    }

  # Return the fetched data as a JSON response
  return Response(json.dumps(data, sort_keys=False),
                  mimetype='application/json')


@app.route('/.well-known/ai-plugin.json')
def serve_ai_plugin():
  return send_from_directory('.',
                             'ai-plugin.json',
                             mimetype='application/json')


@app.route('/.well-known/openapi.yaml')
def serve_openapi_yaml():
  return send_from_directory('.', 'openapi.yaml', mimetype='text/yaml')


if __name__ == '__main__':
  app.run(debug=True, host='0.0.0.0', port=443)
