import { ref } from 'vue'
import { useToast } from '@/composables/useToast'

/**
 * Copy JSON data to clipboard with label feedback.
 */
export function useCopyJson() {
  const { toast } = useToast()
  const copyLabel = ref('Copy JSON')

  async function copy(data: unknown, label = 'Data') {
    try {
      await navigator.clipboard.writeText(JSON.stringify(data, null, 2))
      copyLabel.value = 'Copied!'
      toast(`${label} copied to clipboard`, 'success')
      setTimeout(() => { copyLabel.value = 'Copy JSON' }, 1500)
    } catch {
      toast('Failed to copy', 'error')
    }
  }

  return { copyLabel, copy }
}
