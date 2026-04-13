import { create } from 'zustand'

export interface Block {
	id: number
	content: string
	bbox: [number, number, number, number] | null
	pageIndex: number
	isImage?: boolean
	width: number
	height: number
}

interface OcrStore {
	hoveredBlockId: number | null  // 悬停的 block id
	clickedBlockId: number | null  // 点击的 block id
	clickedPdfBlockId: number | null
	blocks: Block[]
	setHoveredBlockId: (blockId: number | null) => void
	setClickedBlockId: (blockId: number | null) => void
	setClickedPdfBlockId: (blockId: number | null) => void
	setBlocks: (blocks: Block[]) => void
}

export const useOcrStore = create<OcrStore>(set => ({
	hoveredBlockId: null,
	clickedBlockId: null,
	clickedPdfBlockId: null,
	blocks: [],
	setHoveredBlockId: blockId =>
		set({ hoveredBlockId: blockId, clickedBlockId: null, clickedPdfBlockId: null }),
	setClickedBlockId: blockId => set({ clickedBlockId: blockId, hoveredBlockId: blockId }),
	setClickedPdfBlockId: blockId => set({ clickedPdfBlockId: blockId, hoveredBlockId: blockId }),
	setBlocks: blocks => set({ blocks })
}))
