
season <- function(x) 
{
  # Calculates seasonal multiplicative 
  # component of time series with weekly data.
  t <- ts(x,frequency=52)
  res <- decompose(t,type="multiplicative")
  #seas <- res$seasonal
  #seas <- as.vector(seas)
  #return(seas)
  return(res)
}

show_decompose <- function(x)
{
  t <- ts(x,frequency=52)
  res <- decompose(t,type="multiplicative")
  plot(res)
  seas <- res$seasonal
  seas <- as.vector(seas)
  return(seas)
}
