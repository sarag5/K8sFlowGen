"use strict";
var __awaiter = (this && this.__awaiter) || function (thisArg, _arguments, P, generator) {
    function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.deactivate = exports.activate = void 0;
const vscode = require("vscode");
const path = require("path");
const cp = require("child_process");
function activate(context) {
    let disposable = vscode.commands.registerCommand('k8s-flowchart-generator.generateFlowchart', () => __awaiter(this, void 0, void 0, function* () {
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
            const panel = vscode.window.createWebviewPanel('k8sFlowchart', 'K8s Flowchart', vscode.ViewColumn.Two, {});
            panel.webview.html = getWebviewContent(flowchartData);
        }
        catch (error) {
            vscode.window.showErrorMessage(`Error generating flowchart: ${error}`);
        }
    }));
    context.subscriptions.push(disposable);
}
exports.activate = activate;
function getWebviewContent(flowchartData) {
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
function deactivate() { }
exports.deactivate = deactivate;
//# sourceMappingURL=extension.js.map