export type NivelConhecimento = 'zero' | 'basico' | 'intermediario' | 'avancado';
export type OrcamentoPref = 'gratuito' | 'aberto_a_investimentos';
export type IdiomaPref = 'apenas_portugues' | 'aceita_ingles' | 'aceita_outros';
export type RotinaPref = 'prefere_ler' | 'prefere_ouvir' | 'prefere_assistir';
export type MotivacaoPref = 'carreira' | 'hobby' | 'curiosidade' | 'repertorio_social';

export interface PerfilSessao {
  nivel?: NivelConhecimento;
  orcamento?: OrcamentoPref;
  idioma?: IdiomaPref;
  rotina?: RotinaPref;
  motivacao?: MotivacaoPref;
  atualizado_em?: string;
}

export interface ContextoUsuario {
  nivel?: NivelConhecimento;
  orcamento?: OrcamentoPref;
  idioma?: IdiomaPref;
  rotina?: RotinaPref;
  localizacao?: string;
  motivacao?: MotivacaoPref;
}
