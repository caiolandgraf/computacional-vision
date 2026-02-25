import { ref, shallowRef } from 'vue'
import { useToast } from '@/components/ToastNotification.vue'

/**
 * Composable para chamadas de API padronizadas com integração de toast notifications.
 *
 * Encapsula o padrão comum: loading state, error handling, success/error toasts.
 *
 * Uso:
 *   const { data, loading, error, execute } = useApi(analyzeImage)
 *
 *   // Chamada simples
 *   await execute(file, { method: 'combined' })
 *
 *   // Com callbacks
 *   await execute(file, { method: 'combined' }, {
 *     successMessage: 'Análise concluída!',
 *     onSuccess: (result) => { ... },
 *   })
 */
export function useApi(apiFn, options = {}) {
  const {
    /** Mensagem de sucesso padrão (vazio = sem toast de sucesso) */
    successMessage = '',
    /** Mensagem de erro padrão (vazio = usa mensagem do erro) */
    errorMessage = '',
    /** Mostrar toast de erro automaticamente */
    showErrorToast = true,
    /** Mostrar toast de sucesso automaticamente */
    showSuccessToast = false,
    /** Reseta data antes de cada chamada */
    resetOnExecute = true,
    /** Valor inicial de data */
    initialData = null,
    /** Transformação aplicada ao resultado antes de armazenar */
    transform = null,
  } = options

  const data = shallowRef(initialData)
  const loading = ref(false)
  const error = ref(null)
  const toast = useToast()

  /**
   * Executa a chamada de API.
   *
   * @param  {...any} args - Argumentos passados para a função de API
   * @param {Object} [callOptions] - Se o último argumento é um objeto com _apiOptions: true
   * @returns {Promise<{ data: any, error: any }>}
   */
  async function execute(...args) {
    // Extrai opções de chamada se o último argumento tiver _apiOptions
    let callOpts = {}
    if (args.length > 0 && args[args.length - 1]?._apiOptions === true) {
      callOpts = args.pop()
    }

    const {
      successMessage: callSuccess = successMessage,
      errorMessage: callError = errorMessage,
      showErrorToast: callShowError = showErrorToast,
      showSuccessToast: callShowSuccess = showSuccessToast,
      onSuccess = null,
      onError = null,
      transform: callTransform = transform,
    } = callOpts

    loading.value = true
    error.value = null
    if (resetOnExecute) {
      data.value = initialData
    }

    try {
      let result = await apiFn(...args)

      // Aplica transformação se definida
      if (callTransform && typeof callTransform === 'function') {
        result = callTransform(result)
      }

      data.value = result

      // Toast de sucesso
      if (callShowSuccess && callSuccess) {
        toast.success(callSuccess)
      }

      // Callback de sucesso
      if (onSuccess && typeof onSuccess === 'function') {
        onSuccess(result)
      }

      return { data: result, error: null }
    } catch (err) {
      const msg = err?.message || callError || 'Erro desconhecido na requisição'
      error.value = msg

      // Toast de erro
      if (callShowError) {
        toast.error(callError || 'Erro na requisição', msg !== (callError || 'Erro na requisição') ? msg : '')
      }

      // Callback de erro
      if (onError && typeof onError === 'function') {
        onError(err)
      }

      return { data: null, error: msg }
    } finally {
      loading.value = false
    }
  }

  /**
   * Reseta o estado para os valores iniciais.
   */
  function reset() {
    data.value = initialData
    loading.value = false
    error.value = null
  }

  return {
    data,
    loading,
    error,
    execute,
    reset,
  }
}

/**
 * Composable para múltiplas chamadas de API em sequência ou paralelo.
 *
 * Uso:
 *   const { loading, errors, executeAll, executeSequential } = useApiGroup()
 *
 *   await executeAll([
 *     () => checkHealth(),
 *     () => listResults(),
 *     () => listVideoJobs(),
 *   ])
 */
export function useApiGroup() {
  const loading = ref(false)
  const errors = ref([])
  const results = shallowRef([])
  const toast = useToast()

  /**
   * Executa todas as funções em paralelo (Promise.allSettled).
   *
   * @param {Array<Function>} fns - Array de funções que retornam Promises
   * @param {Object} options - Opções
   * @returns {Promise<Array<{status, value?, reason?}>>}
   */
  async function executeAll(fns, options = {}) {
    const {
      showErrors = true,
      errorTitle = 'Erro ao carregar dados',
    } = options

    loading.value = true
    errors.value = []
    results.value = []

    try {
      const settled = await Promise.allSettled(fns.map((fn) => fn()))

      const resultValues = []
      const errorMessages = []

      settled.forEach((result, index) => {
        if (result.status === 'fulfilled') {
          resultValues.push(result.value)
        } else {
          const msg = result.reason?.message || `Erro na operação ${index + 1}`
          errorMessages.push(msg)
          resultValues.push(null)
        }
      })

      results.value = resultValues
      errors.value = errorMessages

      if (showErrors && errorMessages.length > 0) {
        toast.warning(errorTitle, `${errorMessages.length} erro(s): ${errorMessages[0]}`)
      }

      return settled
    } catch (err) {
      const msg = err?.message || 'Erro desconhecido'
      errors.value = [msg]
      if (showErrors) {
        toast.error(errorTitle, msg)
      }
      return []
    } finally {
      loading.value = false
    }
  }

  /**
   * Executa as funções em sequência (uma após a outra).
   *
   * @param {Array<Function>} fns - Array de funções que retornam Promises
   * @param {Object} options - Opções
   * @returns {Promise<Array<any>>}
   */
  async function executeSequential(fns, options = {}) {
    const {
      showErrors = true,
      stopOnError = false,
      errorTitle = 'Erro ao carregar dados',
    } = options

    loading.value = true
    errors.value = []
    results.value = []

    const resultValues = []
    const errorMessages = []

    try {
      for (let i = 0; i < fns.length; i++) {
        try {
          const result = await fns[i]()
          resultValues.push(result)
        } catch (err) {
          const msg = err?.message || `Erro na operação ${i + 1}`
          errorMessages.push(msg)
          resultValues.push(null)

          if (stopOnError) {
            break
          }
        }
      }

      results.value = resultValues
      errors.value = errorMessages

      if (showErrors && errorMessages.length > 0) {
        toast.warning(errorTitle, `${errorMessages.length} erro(s) durante o processamento`)
      }

      return resultValues
    } catch (err) {
      const msg = err?.message || 'Erro desconhecido'
      errors.value = [msg]
      if (showErrors) {
        toast.error(errorTitle, msg)
      }
      return resultValues
    } finally {
      loading.value = false
    }
  }

  function reset() {
    loading.value = false
    errors.value = []
    results.value = []
  }

  return {
    loading,
    errors,
    results,
    executeAll,
    executeSequential,
    reset,
  }
}

/**
 * Helper para criar opções de chamada inline no execute().
 *
 * Uso:
 *   await execute(file, opts, apiOpts({ successMessage: 'OK!' }))
 */
export function apiOpts(options) {
  return { ...options, _apiOptions: true }
}

export default useApi
