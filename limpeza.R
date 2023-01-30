require(readxl)
dadospmu <- read_excel("DOMICILIAR_Consolidados.xlsx")

require(tidyverse)

dadospmu <- dadospmu %>%
  filter(RA_origem != "RIDE - Águas Lindas de Goiás") %>%
  filter(RA_origem != "RIDE - Alexânia") %>%
  filter(RA_origem != "RIDE - Cidade Ocidental") %>%
  filter(RA_origem != "RIDE - Buritis") %>%
  filter(RA_origem != "RIDE - Cocalzinho de Goiás") %>%
  filter(RA_origem != "RIDE - Corumbá de Goiás") %>%
  filter(RA_origem != "RIDE - Cristalina") %>%
  filter(RA_origem != "RIDE - Formosa") %>%
  filter(RA_origem != "RIDE - Luziânia") %>%
  filter(RA_origem != "RIDE - Novo Gama") %>%
  filter(RA_origem != "RIDE - Padre Bernardo") %>%
  filter(RA_origem != "RIDE - Pirenópolis") %>%
  filter(RA_origem != "RIDE - Planaltina-GO") %>%
  filter(RA_origem != "RIDE - Santo Antônio do Descoberto") %>%
  filter(RA_origem != "RIDE - Unaí") %>%
  filter(RA_origem != "RIDE - Valparaíso de Goiás") %>%
  filter(RA_origem != "RIDE - Vila Boa") %>%
  filter(RA_origem != "Externa") %>%
  filter(RA_destino != "RIDE - Águas Lindas de Goiás") %>%
  filter(RA_destino != "RIDE - Alexânia") %>%
  filter(RA_destino != "RIDE - Cidade Ocidental") %>%
  filter(RA_destino != "RIDE - Buritis") %>%
  filter(RA_destino != "RIDE - Cocalzinho de Goiás") %>%
  filter(RA_destino != "RIDE - Corumbá de Goiás") %>%
  filter(RA_destino != "RIDE - Cristalina") %>%
  filter(RA_destino != "RIDE - Formosa") %>%
  filter(RA_destino != "RIDE - Luziânia") %>%
  filter(RA_destino != "RIDE - Novo Gama") %>%
  filter(RA_destino != "RIDE - Padre Bernardo") %>%
  filter(RA_destino != "RIDE - Pirenópolis") %>%
  filter(RA_destino != "RIDE - Planaltina-GO") %>%
  filter(RA_destino != "RIDE - Santo Antônio do Descoberto") %>%
  filter(RA_destino != "RIDE - Unaí") %>%
  filter(RA_destino != "RIDE - Valparaíso de Goiás") %>%
  filter(RA_destino != "RIDE - Vila Boa") %>%
  filter(RA_destino != "RIDE - Cabeceira Grande") %>% 
  filter(RA_destino != "Externa") 

dadospmu$RA_origem[dadospmu$RA_origem == "Águas Claras"] <- "Águas Claras - DF"
dadospmu$RA_origem[dadospmu$RA_origem == "Águas Claras Vertical"] <- "Águas Claras - DF"
dadospmu$RA_origem[dadospmu$RA_origem == "Brazlândia"] <- "Brazlândia - DF"
dadospmu$RA_origem[dadospmu$RA_origem == "Candangolândia"] <- "Candangolândia - DF"
dadospmu$RA_origem[dadospmu$RA_origem == "Ceilândia"] <- "Ceilândia - DF"
dadospmu$RA_origem[dadospmu$RA_origem == "Cruzeiro"] <- "Cruzeiro - DF"
dadospmu$RA_origem[dadospmu$RA_origem == "Fercal"] <- "Fercal - DF"
dadospmu$RA_origem[dadospmu$RA_origem == "Gama"] <- "Gama - DF"
dadospmu$RA_origem[dadospmu$RA_origem == "Guará"] <- "Guará - DF"
dadospmu$RA_origem[dadospmu$RA_origem == "Itapoã"] <- "Itapoã - DF"
dadospmu$RA_origem[dadospmu$RA_origem == "Jardim Botânico"] <- "Jardim Botânico - DF"
dadospmu$RA_origem[dadospmu$RA_origem == "Lago Norte"] <- "Lago Norte - DF"
dadospmu$RA_origem[dadospmu$RA_origem == "Lago Sul"] <- "Lago Sul - DF"
dadospmu$RA_origem[dadospmu$RA_origem == "Núcleo Bandeirante"] <- "Núcleo Bandeirante - DF"
dadospmu$RA_origem[dadospmu$RA_origem == "Paranoá"] <- "Paranoá - DF"
dadospmu$RA_origem[dadospmu$RA_origem == "Park Way"] <- "Park Way - DF"
dadospmu$RA_origem[dadospmu$RA_origem == "Planaltina"] <- "Planaltina - DF"
dadospmu$RA_origem[dadospmu$RA_origem == "Plano Piloto"] <- "Plano Piloto - DF"
dadospmu$RA_origem[dadospmu$RA_origem == "Recanto das Emas"] <- "Recanto das Emas - DF"
dadospmu$RA_origem[dadospmu$RA_origem == "Riacho Fundo I"] <- "Riacho Fundo I - DF"
dadospmu$RA_origem[dadospmu$RA_origem == "Riacho Fundo II"] <- "Riacho Fundo II - DF"
dadospmu$RA_origem[dadospmu$RA_origem == "Samambaia"] <- "Samambaia - DF"
dadospmu$RA_origem[dadospmu$RA_origem == "Santa Maria"] <- "Santa Maria - DF"
dadospmu$RA_origem[dadospmu$RA_origem == "São Sebastião"] <- "NSão Sebastião - DF"
dadospmu$RA_origem[dadospmu$RA_origem == "SCIA/Estrutural"] <- "SCIA - DF"
dadospmu$RA_origem[dadospmu$RA_origem == "SIA"] <- "SIA - DF"
dadospmu$RA_origem[dadospmu$RA_origem == "Sobradinho"] <- "Sobradinho - DF"
dadospmu$RA_origem[dadospmu$RA_origem == "Sobradinho II"] <- "Sobradinho II - DF"
dadospmu$RA_origem[dadospmu$RA_origem == "Sol Nascente/Pôr do Sol"] <- "Sol Nascente/Pôr do Sol - DF"
dadospmu$RA_origem[dadospmu$RA_origem == "Sudoeste/Octogonal"] <- "Sudoeste/Octogonal - DF"
dadospmu$RA_origem[dadospmu$RA_origem == "Taguatinga"] <- "Taguatinga - DF"
dadospmu$RA_origem[dadospmu$RA_origem == "Varjão"] <- "Varjão - DF"
dadospmu$RA_origem[dadospmu$RA_origem == "Vicente Pires"] <- "Vicente Pires - DF"

dadospmu$RA_destino[dadospmu$RA_destino == "Águas Claras"] <- "Águas Claras - DF"
dadospmu$RA_destino[dadospmu$RA_destino == "Águas Claras Vertical"] <- "Águas Claras - DF"
dadospmu$RA_destino[dadospmu$RA_destino == "Brazlândia"] <- "Brazlândia - DF"
dadospmu$RA_destino[dadospmu$RA_destino == "Candangolândia"] <- "Candangolândia - DF"
dadospmu$RA_destino[dadospmu$RA_destino == "Ceilândia"] <- "Ceilândia - DF"
dadospmu$RA_destino[dadospmu$RA_destino == "Cruzeiro"] <- "Cruzeiro - DF"
dadospmu$RA_destino[dadospmu$RA_destino == "Fercal"] <- "Fercal - DF"
dadospmu$RA_destino[dadospmu$RA_destino == "Gama"] <- "Gama - DF"
dadospmu$RA_destino[dadospmu$RA_destino == "Guará"] <- "Guará - DF"
dadospmu$RA_destino[dadospmu$RA_destino == "Itapoã"] <- "Itapoã - DF"
dadospmu$RA_destino[dadospmu$RA_destino == "Jardim Botânico"] <- "Jardim Botânico - DF"
dadospmu$RA_destino[dadospmu$RA_destino == "Lago Norte"] <- "Lago Norte - DF"
dadospmu$RA_destino[dadospmu$RA_destino == "Lago Sul"] <- "Lago Sul - DF"
dadospmu$RA_destino[dadospmu$RA_destino == "Núcleo Bandeirante"] <- "Núcleo Bandeirante - DF"
dadospmu$RA_destino[dadospmu$RA_destino == "Paranoá"] <- "Paranoá - DF"
dadospmu$RA_destino[dadospmu$RA_destino == "Park Way"] <- "Park Way - DF"
dadospmu$RA_destino[dadospmu$RA_destino == "Planaltina"] <- "Planaltina - DF"
dadospmu$RA_destino[dadospmu$RA_destino == "Plano Piloto"] <- "Plano Piloto - DF"
dadospmu$RA_destino[dadospmu$RA_destino == "Recanto das Emas"] <- "Recanto das Emas - DF"
dadospmu$RA_destino[dadospmu$RA_destino == "Riacho Fundo I"] <- "Riacho Fundo I - DF"
dadospmu$RA_destino[dadospmu$RA_destino == "Riacho Fundo II"] <- "Riacho Fundo II - DF"
dadospmu$RA_destino[dadospmu$RA_destino == "Samambaia"] <- "Samambaia - DF"
dadospmu$RA_destino[dadospmu$RA_destino == "Santa Maria"] <- "Santa Maria - DF"
dadospmu$RA_destino[dadospmu$RA_destino == "São Sebastião"] <- "NSão Sebastião - DF"
dadospmu$RA_destino[dadospmu$RA_destino == "SCIA/Estrutural"] <- "SCIA - DF"
dadospmu$RA_destino[dadospmu$RA_destino == "SIA"] <- "SIA - DF"
dadospmu$RA_destino[dadospmu$RA_destino == "Sobradinho"] <- "Sobradinho - DF"
dadospmu$RA_destino[dadospmu$RA_destino == "Sobradinho II"] <- "Sobradinho II - DF"
dadospmu$RA_destino[dadospmu$RA_destino == "Sol Nascente/Pôr do Sol"] <- "Sol Nascente/Pôr do Sol - DF"
dadospmu$RA_destino[dadospmu$RA_destino == "Sudoeste/Octogonal"] <- "Sudoeste/Octogonal - DF"
dadospmu$RA_destino[dadospmu$RA_destino == "Taguatinga"] <- "Taguatinga - DF"
dadospmu$RA_destino[dadospmu$RA_destino == "Varjão"] <- "Varjão - DF"
dadospmu$RA_destino[dadospmu$RA_destino == "Vicente Pires"] <- "Vicente Pires - DF"

dadospmu$RA_destino[dadospmu$RA_destino == "NSão Sebastião - DF"] <- "São Sebastião - DF"
dadospmu$RA_origem[dadospmu$RA_origem == "NSão Sebastião - DF"] <- "São Sebastião - DF"
