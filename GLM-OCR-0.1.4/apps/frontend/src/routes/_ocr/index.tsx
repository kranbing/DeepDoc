import { createFileRoute } from '@tanstack/react-router'
import { OCRPage } from './OCRPage'

export const Route = createFileRoute('/_ocr/')({
	component: OCRPage
})
