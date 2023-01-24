#aqui dentro da função setwd vc põe o caminho da pasta onde vc salvar no seu computador

setwd("C:/Users/betha/OneDrive/Documentos/resilienciapibic")

install.package("readxl")

require(readxl)
require(tidyverse)
require(openxlsx)

dadospmu <- read_excel("DOMICILIAR_Consolidados.xlsx")
matrizod <- read_excel("matrizdistanciapelogmaps.xlsx")

dadospmu <- dadospmu %>%
  mutate(tempoviagem = substr(tempoviagem, 12, 16))

viagensentreras <- dadospmu %>%
  group_by(RA_origem, RA_destino) %>%
  summarise(
    totaldeviagens = n()
  )

ped <- dadospmu %>% 
  group_by(modoagregado2, RA_origem, RA_destino) %>%
  summarise(
    totaldeviagens = n()
  ) %>% 
  filter(modoagregado2 %in% c("TA_aPe"))

cic <- dadospmu %>% 
  group_by(modoagregado2, RA_origem, RA_destino) %>%
  summarise(
    totaldeviagens = n()
  ) %>% 
  filter(modoagregado2 %in% c("TA_Bicicleta"))

tc <- dadospmu %>% 
  group_by(modoagregado1, RA_origem, RA_destino) %>%
  summarise(
    totaldeviagens = n()
  ) %>% 
  filter(modoagregado1 %in% c("TC"))

ti <- dadospmu %>% 
  group_by(modoagregado1, RA_origem, RA_destino) %>%
  summarise(
    totaldeviagens = n()
  ) %>% 
  filter(modoagregado1 %in% c("TI"))

write.xlsx(ped,"dadospmuTape.xlsx",colNames = TRUE)
write.xlsx(tc,"dadospmuTC.xlsx",colNames = TRUE)
write.xlsx(ti,"dadospmuTI.xlsx",colNames = TRUE)
write.xlsx(cic,"dadospmuTbic.xlsx",colNames = TRUE)
write.xlsx(viagensentreras,"viagnesentreras.xlsx",colNames = TRUE)
