const fs = require('fs');
const path = require('path');

function trackCost() {
  try {
    const input = fs.readFileSync(0, 'utf8');
    if (!input) {
      return;
    }

    const toolCall = JSON.parse(input);
    const { tool, arguments: args } = toolCall;
    const metricsPath = path.join(process.cwd(), 'gemini_metrics.csv');

    // Ensure CSV header exists
    if (!fs.existsSync(metricsPath)) {
      fs.writeFileSync(metricsPath, 'timestamp,tool,arguments,input_tokens_est,output_tokens_est,cost_est
');
    }

    const timestamp = new Date().toISOString();
    const argsString = JSON.stringify(args).replace(/"/g, '""'); // CSV escape

    // Basic heuristic: length of arguments for token estimation
    const inputTokensEst = Math.ceil(argsString.length / 4);
    const costEst = (inputTokensEst / 1000000) * 0.10; // Gemini 2.0 Flash estimate

    const logLine = `${timestamp},${tool},"${argsString}",${inputTokensEst},0,${costEst.toFixed(6)}
`;
    fs.appendFileSync(metricsPath, logLine);

  } catch (error) {
    process.stderr.write(`Cost tracking hook error: ${error.message}
`);
  }
}

trackCost();
