import { visit } from 'unist-util-visit'

export function remarkSideNotes() {
    return (tree) => {
        const definitions = new Map()

        visit(tree, 'footnoteDefinition', (node) => {
            definitions.set(node.identifier, node.children)
        })

        visit(tree, 'footnoteReference', (node, index, parent) => {
            const children = definitions.get(node.identifier)

            if (children) {
                let content = children
                if (content.length > 0 && content[0].type === 'paragraph') {
                    content = content[0].children
                }

                const textContent = content
                    .map(c => c.value || '')
                    .join('')

                const sideNoteNode = {
                    type: 'text',
                    value: ''
                }
                sideNoteNode.data = {
                    hName: 'span',
                    hProperties: { className: 'sidenote' },
                    hChildren: [
                        {
                            type: 'text',
                            value: ''
                        },
                        {
                            type: 'element',
                            tagName: 'span',
                            properties: { className: ['sidenote-number'] },
                            children: [{ type: 'text', value: node.label || node.identifier }]
                        },
                        { type: 'text', value: ` ${textContent}` }
                    ]
                }

                parent.children.splice(index, 1, sideNoteNode)
            }
        })

        const newChildren = tree.children.filter(node => node.type !== 'footnoteDefinition')
        tree.children = newChildren
    }
}
