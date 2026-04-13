/**
 * Rehype plugin: parse `$...$` / `$$...$$` appearing in raw HTML (e.g. `<table>`)
 * into nodes that `rehype-katex` can render.
 *
 * Why needed:
 * - `remark-math` does not parse math inside raw HTML blocks.
 * - `rehype-raw` turns raw HTML into HAST, but math is still plain text.
 * - `rehype-katex` only renders elements with className including:
 *   - `language-math` and (`math-inline` | `math-display`)
 */
export default function rehypeMathInHtml() {
	return function transformer(tree: any) {
		walk(tree, [])
	}
}

const SKIP_TAGS = new Set([
	// Do not parse math in code-like contexts.
	'code',
	'pre',
	'kbd',
	'samp',
	// Raw/unsafe contexts.
	'script',
	'style',
	'textarea'
])

function walk(node: any, ancestors: any[]) {
	if (!node) return

	if (node.type === 'element') {
		if (typeof node.tagName === 'string' && SKIP_TAGS.has(node.tagName)) return

		const nextAncestors = ancestors.concat(node)
		const children = Array.isArray(node.children) ? node.children : null
		if (!children || children.length === 0) return

		const next: any[] = []
		for (const child of children) {
			if (child?.type === 'text' && typeof child.value === 'string') {
				const parts = splitTextWithMath(child.value)
				if (parts.length === 1 && parts[0]?.type === 'text' && parts[0].value === child.value) {
					next.push(child)
				} else {
					next.push(...parts)
				}
			} else {
				next.push(child)
				walk(child, nextAncestors)
			}
		}

		node.children = next
		return
	}

	// Root / other nodes.
	const children = Array.isArray(node.children) ? node.children : null
	if (children && children.length) {
		for (const child of children) walk(child, ancestors)
	}
}

function splitTextWithMath(value: string): any[] {
	// Fast path.
	if (!value.includes('$')) return [{ type: 'text', value }]

	const out: any[] = []
	let buffer = ''
	let i = 0

	const flushBuffer = () => {
		if (buffer) out.push({ type: 'text', value: buffer })
		buffer = ''
	}

	while (i < value.length) {
		const ch = value[i]

		// Escaped dollar: keep literal.
		if (ch === '\\' && value[i + 1] === '$') {
			buffer += '\\$'
			i += 2
			continue
		}

		if (ch !== '$') {
			buffer += ch
			i += 1
			continue
		}

		// Display math: $$...$$
		if (value[i + 1] === '$' && !isEscapedAt(value, i)) {
			const close = findUnescaped(value, '$$', i + 2)
			if (close !== -1) {
				const expr = value.slice(i + 2, close)
				// Avoid converting empty blocks like `$$$$`.
				if (expr.trim().length > 0) {
					flushBuffer()
					out.push(makeMathCode(expr, true))
					i = close + 2
					continue
				}
			}
		}

		// Inline math: $...$
		if (!isEscapedAt(value, i)) {
			const close = findUnescaped(value, '$', i + 1)
			if (close !== -1) {
				const expr = value.slice(i + 1, close)
				if (expr.trim().length > 0) {
					flushBuffer()
					out.push(makeMathCode(expr, false))
					i = close + 1
					continue
				}
			}
		}

		// Fallback: treat as literal `$`.
		buffer += '$'
		i += 1
	}

	flushBuffer()
	return out.length ? out : [{ type: 'text', value }]
}

function makeMathCode(expr: string, display: boolean) {
	return {
		type: 'element',
		tagName: 'code',
		properties: {
			className: ['language-math', display ? 'math-display' : 'math-inline']
		},
		children: [{ type: 'text', value: expr }]
	}
}

function isEscapedAt(text: string, index: number) {
	// Count preceding backslashes: odd = escaped.
	let count = 0
	for (let i = index - 1; i >= 0 && text[i] === '\\'; i--) count++
	return count % 2 === 1
}

function findUnescaped(text: string, needle: string, fromIndex: number) {
	let i = fromIndex
	while (i < text.length) {
		const idx = text.indexOf(needle, i)
		if (idx === -1) return -1
		if (!isEscapedAt(text, idx)) return idx
		i = idx + needle.length
	}
	return -1
}
