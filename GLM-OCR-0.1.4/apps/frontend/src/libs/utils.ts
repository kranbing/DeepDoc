import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}


// 复制函数（纯 JS/TS，可直接用在任何 React/Next.js 项目）
export function copyToClipboard(text: string): Promise<boolean> {
  if (!text) return Promise.resolve(false)
  // 优先尝试现代 Clipboard API（只在 HTTPS 下有效）
  if (navigator.clipboard && window.isSecureContext) {
    return navigator.clipboard
      .writeText(text)
      .then(() => true)
      .catch(() => fallbackCopy(text));
  }

  // HTTP 或不支持 clipboard API 时走经典降级方案
  return fallbackCopy(text);
}

// 经典降级方案：创建隐藏 textarea + execCommand
function fallbackCopy(text: string): Promise<boolean> {
  return new Promise((resolve) => {
    const textArea = document.createElement('textarea');
    
    // 防止滚动跳动 + 移动端键盘弹出
    textArea.value = text;
    textArea.style.position = 'fixed';
    textArea.style.top = '0';
    textArea.style.left = '0';
    textArea.style.opacity = '0';
    textArea.style.pointerEvents = 'none'; // 防止干扰点击
    
    // 兼容 iOS 需要这个
    textArea.setAttribute('readonly', 'true');
    
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();

    try {
      const successful = document.execCommand('copy');
      resolve(successful);
    } catch (err) {
      console.error('复制失败:', err);
      resolve(false);
    } finally {
      document.body.removeChild(textArea);
    }
  });
}