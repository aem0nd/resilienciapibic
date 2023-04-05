setwd("C:/Users/betha/OneDrive/Documentos/resilienciapibic")

library(cartography)
library(sf)
library(tidyverse)
library(ggthemes)

map <- st_read('mapres.shp')

library(haven)
library(rgdal)
library(sp)
library(ggspatial)

points <- cbind(map, st_coordinates(st_centroid(map$geometry)))

ggplot() +
  geom_sf(data = map, aes(fill = cenario.5)) +
  scale_fill_gradient(low = "white",
                      high = "blue",
                      limits = c(0, 100)) +
  geom_text(data = points, aes(x = X, y = Y, label = paste(ra_num)),
            color = 'black', size = 3) +
  labs(title = '',
       subtitle = 'Cenario 5',
       x = 'Longitude',
       y = 'Latitude') +
  annotation_scale(location = "tl") +
  annotation_north_arrow(location = "br", which_north = "true")
