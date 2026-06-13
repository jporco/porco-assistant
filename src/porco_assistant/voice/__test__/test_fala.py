from porco_assistant.voice.core.fala import limpar_para_fala, resumir_para_fala


def test_remove_markdown():
    t = limpar_para_fala("**Pronto** com `codigo` e *italico*")
    assert "Pronto" in t
    assert "`" not in t
    assert "*" not in t


def test_remove_link_e_path():
    t = limpar_para_fala("Veja [aqui](https://x.com) em /home/user/project/foo")
    assert "http" not in t
    assert "/mnt" not in t
    assert "aqui" in t


def test_ignora_lixo():
    assert limpar_para_fala("...") == ""
    assert limpar_para_fala("   ") == ""


def test_resumo_frases():
    t = resumir_para_fala("Primeira frase. Segunda frase. Terceira longa demais.")
    assert "Primeira" in t
    assert "Segunda" in t
