import { WithContext } from 'schema-dts'

function JsonLd<T>(json: WithContext<T>): string {
  return `<script type="application/ld+json">${JSON.stringify(json)}</script>`
}

function JsonLdList<T>(jsonList: WithContext<T>[]): string {
  return jsonList
    .map((json) => `<script type="application/ld+json">${JSON.stringify(json)}</script>`)
    .join('\n')
}

export { JsonLdList, JsonLd }
