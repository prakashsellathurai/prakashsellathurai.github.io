import { visit } from 'unist-util-visit'

export function remarkSideNotes() {
    return (tree) => {
        const definitions = new Map()

        // 1. Collect all definitions
        visit(tree, 'footnoteDefinition', (node) => {
            definitions.set(node.identifier, node.children)
        })

        // 2. Transform references to SideNote components
        visit(tree, 'footnoteReference', (node, index, parent) => {
            const children = definitions.get(node.identifier)

            if (children) {
                // Create the JSX node for <SideNote>
                // Unwrap the first paragraph to avoid <p> inside <span> (SideNote is inline)
                let content = children
                if (content.length > 0 && content[0].type === 'paragraph') {
                    content = content[0].children
                }

                // Construct the MdxJsxTextElement node
                const sideNoteNode = {
                    type: 'mdxJsxTextElement',
                    name: 'SideNote',
                    attributes: [
                        {
                            type: 'mdxJsxAttribute',
                            name: 'title',
                            value: node.label || node.identifier,
                        },
                    ],
                    children: content,
                }

                parent.children.splice(index, 1, sideNoteNode)
            }
        })

        // 3. Remove definitions from the tree
        // We filter them out or replace them with empty nodes.
        // Filtering is safer in a separate pass or simpler way.

        const newChildren = tree.children.filter(node => node.type !== 'footnoteDefinition')
        tree.children = newChildren
    }
}
