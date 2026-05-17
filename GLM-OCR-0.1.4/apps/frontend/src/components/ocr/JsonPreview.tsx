import JsonView from "@uiw/react-json-view"

export function JsonPreview({ json }: { json: any }) {
    return (
        <JsonView
            value={json}
            style={{
                backgroundColor: 'transparent',
                fontSize: '0.875rem',
                fontFamily:
                    'source-code-pro, Menlo, Monaco, Consolas, "Courier New", monospace'
            }}
            displayDataTypes={false}
            displayObjectSize={false}
            enableClipboard={false}
        >
            <JsonView.Null
                render={(props: any, ctx: any) => {
                    if (ctx?.type !== 'value') return null
                    return (
                        <span
                            {...props}
                            className='w-rjv-value'
                            style={{
                                ...props?.style,
                                color: 'var(--w-rjv-type-null-color, #d33682)'
                            }}>
                            null
                        </span>
                    )
                }}
            />
            <JsonView.Undefined
                render={(props: any, ctx: any) => {
                    if (ctx?.type !== 'value') return null
                    return (
                        <span
                            {...props}
                            className='w-rjv-value'
                            style={{
                                ...props?.style,
                                color: 'var(--w-rjv-type-undefined-color, #586e75)'
                            }}>
                            undefined
                        </span>
                    )
                }}
            />
        </JsonView>
    )
}