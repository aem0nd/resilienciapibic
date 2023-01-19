#aqui dentro da função setwd vc põe o caminho da pasta onde vc salvar no seu computador

setwd("C:/Users/betha/OneDrive/Documentos/resilienciapibic")

install.package("readxl")

require(readxl)
require(tidyverse)

dadospmu <- read_excel("DOMICILIAR_Consolidados.xlsx")
matrizod <- read_excel("matrizdistanciapelogmaps.xlsx")

dadospmu <- dadospmu %>%
  mutate(tempoviagem = substr(tempoviagem, 12, 16))
