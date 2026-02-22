import { ref, type Ref } from 'vue'

/**
 * Reactive Set with toggle/has/clear helpers.
 * Re-assigns the ref on each mutation to trigger Vue reactivity.
 */
export function useSetToggle<T = string>(initial: Iterable<T> = []) {
  const items: Ref<Set<T>> = ref(new Set(initial)) as Ref<Set<T>>

  function toggle(item: T) {
    const next = new Set(items.value)
    if (next.has(item)) next.delete(item)
    else next.add(item)
    items.value = next
  }

  function has(item: T): boolean {
    return items.value.has(item)
  }

  function clear() {
    items.value = new Set()
  }

  function addAll(newItems: Iterable<T>) {
    items.value = new Set(newItems)
  }

  return { items, toggle, has, clear, addAll }
}
