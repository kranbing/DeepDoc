import { CircleCheck, Info, LoaderCircle, TriangleAlert, XCircleIcon } from 'lucide-react'
import { Toaster as Sonner } from 'sonner'


type ToasterProps = React.ComponentProps<typeof Sonner>

const Toaster = ({ ...props }: ToasterProps) => {
	return (
		<Sonner
			// theme='dark'
			className='toaster group'
			icons={{
				success: <CircleCheck className='h-4 w-4' />,
				info: <Info className='h-4 w-4' />,
				warning: <TriangleAlert className='h-4 w-4' />,
				error: <XCircleIcon className='h-4 w-4' />,
				loading: <LoaderCircle className='h-4 w-4 animate-spin' />
			}}
			toastOptions={{
        duration: 3500,
				classNames: {
					toast: '!static !shadow-lg !rounded-[12px] !px-4 !py-[10px] !gap-1 !w-auto',
					title: '!text-sm leading-[22px] text-white font-normal',
					description: 'text-[14px] leading-[22px] text-white',
					actionButton: 'bg-primary text-primary-foreground',
					cancelButton: 'bg-muted text-muted-foreground',
					closeButton:
						'bg-[#f94242] text-white rounded-[8px] w-4 h-4 opacity-100 hover:opacity-80 [&>svg]:text-white [&>svg]:w-3 [&>svg]:h-3'
				}
			}}
			style={{
				// position: 'fixed',
				top: 40,
        left: '50%',
        transform: 'translateX(-50%)',
				display: 'flex',
				flexDirection: 'column',

				alignItems: 'center',
				width: '100%',
				pointerEvents: 'none'
			}}
			visibleToasts={1}
			{...props}
		/>
	)
}

export { Toaster }
