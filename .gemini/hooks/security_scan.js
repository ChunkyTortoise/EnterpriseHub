const fs = require('fs');

function scan() {
  try {
    const input = fs.readFileSync(0, 'utf8');
    if (!input) {
      console.log(JSON.stringify({ decision: 'allow' }));
      return;
    }

    const toolCall = JSON.parse(input);
    const { tool, arguments: args } = toolCall;

    // Simple security rules
    const sensitivePatterns = [/\.env/, /\.ssh/, /passwd/, /shadow/];
    const argsString = JSON.stringify(args);

    for (const pattern of sensitivePatterns) {
      if (pattern.test(argsString)) {
        console.log(JSON.stringify({
          decision: 'deny',
          reason: `Access to sensitive pattern "${pattern.source}" is restricted.`
        }));
        return;
      }
    }

    // Specific tool checks
    if (tool === 'run_shell_command' && args.command) {
      const dangerousCommands = ['rm -rf /', 'mkfs', 'dd if='];
      for (const cmd of dangerousCommands) {
        if (args.command.includes(cmd)) {
          console.log(JSON.stringify({
            decision: 'deny',
            reason: `Potentially destructive command detected: "${cmd}"`
          }));
          return;
        }
      }
    }

    console.log(JSON.stringify({ decision: 'allow' }));
  } catch (error) {
    // If there's an error parsing or reading, default to allow but maybe log to stderr
    process.stderr.write(`Security scan hook error: ${error.message}
`);
    console.log(JSON.stringify({ decision: 'allow' }));
  }
}

scan();
