install.packages("reticulate",repos = "http://cran.us.r-project.org")
library(reticulate)
py_install("git+https://github.com/gro-intelligence/api-client.git")

gro_client <- import("api.client.gro_client")

groclient = gro_client$GroClient("api.gro-intelligence.com","put-your-api-token-here")

groclient$add_single_data_series(dict(metric_id=570001L, item_id=95L, region_id=1210L, source_id=2L, frequency_id=9L))
print(groclient$get_df())
