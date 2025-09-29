segment <- function(data,dfrom,dto,h,breaks)
{
  t <- ts(data,frequency=7)
  fit <- bfast(t,max.iter=1)
  output <- fit$output
  out <- output[[1]]
  orig = as.vector(out$Vt)
  lntr = as.vector(out$Tt)
  return(list(orig,lntr))
}



