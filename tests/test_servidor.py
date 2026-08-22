

def test_instrucoes_dizem_onde_a_ressalva_tem_de_aparecer():
    """A regra existia e era obedecida — no rodapé.

    Duas rodadas do teste de aceitação abriram com "Sim, continua em vigor" e
    "Não, foi extinto", cada uma com a ressalva correta oito parágrafos abaixo.
    Quem lê a primeira linha e cita não é salvo pelo rodapé.
    """
    from legis.servidor import INSTRUCOES

    assert "oração principal" in INSTRUCOES
    for proibida in ('"sim, está em vigor"', '"não, foi extinta"'):
        assert proibida in INSTRUCOES.lower(), proibida
    # a negativa também é afirmação sobre o mundo
    assert "não localizei norma sobre isso neste acervo" in INSTRUCOES
