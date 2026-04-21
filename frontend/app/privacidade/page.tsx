import type { Metadata } from 'next';

export const metadata: Metadata = { title: 'Política de Privacidade' };

export default function PrivacidadePage() {
  return (
    <article style={{ maxWidth: '72ch', margin: '0 auto', padding: '2rem 1rem' }}>
      <h1>Política de Privacidade</h1>

      <p>
        O CuradorIA foi construído com privacidade como princípio central (LGPD by design).
      </p>

      <h2>Dados coletados</h2>
      <p>
        Não coletamos nenhum dado pessoal identificável (nome, e-mail, telefone).
        Sua sessão é identificada por um cookie seguro e anônimo com validade de 180 dias.
      </p>

      <h2>Cookie de sessão</h2>
      <p>
        Utilizamos um único cookie <code>session_token</code> (HttpOnly, Secure, SameSite=Strict)
        estritamente necessário para salvar e recuperar seus planos de estudo.
        Este cookie não é usado para rastreamento.
      </p>

      <h2>Seus direitos (LGPD — Art. 18)</h2>
      <ul>
        <li>Acesso: você pode exportar todos os seus planos a qualquer momento.</li>
        <li>Deleção: você pode apagar todos os seus dados em Configurações.</li>
        <li>Portabilidade: exportação em formato JSON disponível.</li>
      </ul>

      <h2>Retenção</h2>
      <p>
        Sessões inativas por 180 dias são automaticamente excluídas de forma permanente.
      </p>

      <h2>Contato</h2>
      <p>
        Para exercer seus direitos ou tirar dúvidas, envie e-mail para:{' '}
        <a href="mailto:privacidade@curadoria.app">privacidade@curadoria.app</a>
      </p>
    </article>
  );
}
