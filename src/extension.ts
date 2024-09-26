import * as vscode from 'vscode';
import * as path from 'path';
import * as cp from 'child_process';

export function activate(context: vscode.ExtensionContext) {
  let disposable = vscode.commands.registerCommand('k8s-flowchart-generator.generateFlowchart', async () => {
    const editor = vscode.window.activeTextEditor;
    if (!editor) {
      vscode.window.showErrorMessage('No active editor found');
      return;
    }

    const document = editor.document;
    if (document.languageId !== 'yaml') {
      vscode.window.showErrorMessage('Active file is not a YAML file');
      return;
    }

    const filePath = document.uri.fsPath;
    const pythonPath = vscode.workspace.getConfiguration('k8s-flowchart-generator').get('pythonPath', 'python');
    const scriptPath = path.join(context.extensionPath, 'python', 'k8s_flowchart.py');

    try {
      const result = cp.execSync(`"${pythonPath}" "${scriptPath}" "${filePath}"`, { encoding: 'utf-8' });
      const flowchartData = JSON.parse(result);
      
      // Create and show a new webview
      const panel = vscode.window.createWebviewPanel(
        'k8sFlowchart',
        'K8s Flowchart',
        vscode.ViewColumn.Two,
        {}
      );

      panel.webview.html = getWebviewContent(flowchartData);
    } catch (error) {
      vscode.window.showErrorMessage(`Error generating flowchart: ${error}`);
    }
  });

  context.subscriptions.push(disposable);
}

function getWebviewContent(flowchartData: any) {
  return `<!DOCTYPE html>
  <html lang="en">
  <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>K8s Flowchart</title>
      <script src="https://d3js.org/d3.v6.min.js"></script>
      <style>
          body { font-family: Arial, sans-serif; }
          #chart { width: 100%; height: 600px; }
      </style>
  </head>
  <body>
      <div id="chart"></div>
      <script>
          const data = ${JSON.stringify(flowchartData)};
          // Add your D3.js visualization code here
      </script>
  </body>
  </html>`;
}

export function deactivate() {}