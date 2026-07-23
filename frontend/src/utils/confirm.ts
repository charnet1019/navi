import { Modal } from 'ant-design-vue'

interface ConfirmActionOptions {
  title: string
  content: string
  okText: string
  danger?: boolean
  onOk: () => Promise<void> | void
}

export function confirmAction(options: ConfirmActionOptions): void {
  Modal.confirm({
    title: options.title,
    content: options.content,
    okText: options.okText,
    okType: options.danger ? 'danger' : undefined,
    onOk: options.onOk
  })
}
