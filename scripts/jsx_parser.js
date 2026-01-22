const parser = require('@babel/parser');
const traverse = require('@babel/traverse').default;
const fs = require('fs');

const code = fs.readFileSync(0, 'utf-8');

try {
    const ast = parser.parse(code, {
        sourceType: 'module',
        plugins: ['jsx', 'typescript', 'decorators-legacy', 'classProperties'],
    });

    const chunks = [];
    const imports = [];

    traverse(ast, {
        ImportDeclaration(path) {
            imports.push(code.substring(path.node.start, path.node.end));
        },
        ExportNamedDeclaration(path) {
            if (path.node.declaration) {
                const decl = path.node.declaration;
                let name = '';
                if (decl.type === 'VariableDeclaration') {
                    name = decl.declarations[0].id.name;
                } else if (decl.type === 'FunctionDeclaration' || decl.type === 'ClassDeclaration' || decl.type === 'InterfaceDeclaration' || decl.type === 'TSInterfaceDeclaration' || decl.type === 'TSTypeAliasDeclaration') {
                    name = decl.id.name;
                }

                if (name) {
                    chunks.push({
                        id: name,
                        start: path.node.start,
                        end: path.node.end,
                        type: (decl.type === 'InterfaceDeclaration' || decl.type === 'TSInterfaceDeclaration' || decl.type === 'TSTypeAliasDeclaration') ? 'interface' : 'component'
                    });
                }
            }
        },
        ExportDefaultDeclaration(path) {
             chunks.push({
                id: 'default',
                start: path.node.start,
                end: path.node.end,
                type: 'component'
            });
        }
    });

    const result = chunks.map(chunk => {
        const chunkCode = code.substring(chunk.start, chunk.end);
        const deps = chunks
            .filter(other => other.id !== chunk.id && other.id !== 'default')
            .filter(other => {
                // Simple check for identifier usage
                // In a more robust version, we'd use traverse to find Identifier usage
                return new RegExp(`\b${other.id}\b`).test(chunkCode);
            })
            .map(other => other.id);

        return {
            id: chunk.id,
            code: chunkCode,
            dependencies: deps,
            type: chunk.type
        };
    });

    console.log(JSON.stringify({ chunks: result, imports }));
} catch (e) {
    console.error(e.message);
    process.exit(1);
}
