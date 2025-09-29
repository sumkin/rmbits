library(MASS)
library(Matching)

find_var_prop <- function(x)
{
    SIGN.LVL <- 0.01

    mean <- mean(x)
    var <- var(x)
    sd <- sd(x)

    distr.vec <- find_distr(x)
    distr.name <- distr.vec[1]

    return
    if (distr.name == 'cauchy')
    {
        q.lower = qcauchy(SIGN.LVL, scale=as.real(distr.vec[2]), lower.tail=TRUE)
        q.upper = qcauchy(SIGN.LVL, scale=as.real(distr.vec[2]), lower.tail=FALSE)
    }
    else if (distr.name == 'exp')
    {
        q.lower = qexp(SIGN.LVL, rate=as.real(distr.vec[2]), lower.tail=TRUE)
        q.upper = qexp(SIGN.LVL, rate=as.real(distr.vec[2]), lower.tail=FALSE)
    }
    else if (distr.name == 'gamma')
    {
        q.lower = qgamma(SIGN.LVL, shape=as.real(distr.vec[2]), rate=as.real(distr.vec[3]), lower.tail=TRUE)
        q.upper = qgamma(SIGN.LVL, shape=as.real(distr.vec[2]), rate=as.real(distr.vec[3]), lower.tail=FALSE)
    }
    else if (distr.name == 'geom')
    {
        q.lower = qgeom(SIGN.LVL, prob=as.real(distr.vec[2]), lower.tail=TRUE)
        q.upper = qgeom(SIGN.LVL, prob=as.real(distr.vec[2]), lower.tail=FALSE)
    }
    else if (distr.name == 'lnorm')
    {
        q.lower = qlnorm(SIGN.LVL, meanlog=as.real(distr.vec[2]), sdlog=as.real(distr.vec[3]), lower.tail=TRUE)
        q.upper = qlnorm(SIGN.LVL, meanlog=as.real(distr.vec[2]), sdlog=as.real(distr.vec[3]), lower.tail=FALSE)
    }
    else if (distr.name == 'logis')
    {
        q.lower = qlogis(SIGN.LVL, location=as.real(distr.vec[2]), scale=as.real(distr.vec[3]), lower.tail=TRUE)
        q.upper = qlogis(SIGN.LVL, location=as.real(distr.vec[2]), scale=as.real(distr.vec[3]), lower.tail=FALSE)
    }
    else if (distr.name == 'nbinom')
    {
        q.lower = qnbinom(SIGN.LVL, size=as.real(distr.vec[2]), mu=as.real(distr.vec[3]), lower.tail=TRUE)
        q.upper = qnbinom(SIGN.LVL, size=as.real(distr.vec[2]), mu=as.real(distr.vec[3]), lower.tail=FALSE) 
    }
    else if (distr.name == 'norm')
    {
        q.lower = qnorm(SIGN.LVL, mean=as.real(distr.vec[2]), sd=as.real(distr.vec[3]), lower.tail=TRUE)
        q.upper = qnorm(SIGN.LVL, mean=as.real(distr.vec[2]), sd=as.real(distr.vec[3]), lower.tail=FALSE)
    }
    else if (distr.name == 'pois')
    {
        q.lower = qpois(SIGN.LVL, lambda=as.real(distr.vec[2]), lower.tail=TRUE)
        q.upper = qpois(SIGN.LVL, lambda=as.real(distr.vec[2]), lower.tail=FALSE)
    }
    else if (distr.name == 'weibull')
    {
        q.lower = qweibull(SIGN.LVL, shape=as.real(distr.vec[2]), scale=as.real(distr.vec[3]), lower.tail=TRUE)
        q.upper = qweibull(SIGN.LVL, shape=as.real(distr.vec[2]), scale=as.real(distr.vec[3]), lower.tail=FALSE)
    }
    else
    {
        q.lower <- 0
        q.upper <- 0
    }

    if (q.lower != 0 && q.upper != 0)
    {
        ratio.lower <- (mean - q.lower)/sd
        ratio.upper <- (q.upper - mean)/sd
    }
    else
    {
        ratio.lower <- 0
        ratio.upper <- 0
    }

    ret <- c(ratio.lower, ratio.upper)

    return(ret)
}

find_distr <- function(x)
{
    SIGN.LEVEL <- 0.05
    y <- c()

    # gamma
    res <- fitdistr(x, 'gamma')
    gamma.shape <- as.real(res$estimate[1])
    gamma.rate <- as.real(res$estimate[2])
    y.gamma <- rgamma(length(x),rate=gamma.rate,shape=gamma.shape)
    res.ks.gamma <- ks.boot(x,y.gamma)
    res.chisq.gamma.pval <- rw_chisq(x,y.gamma)
    if (res.ks.gamma$ks.boot.pvalue > SIGN.LEVEL && res.chisq.gamma.pval > SIGN.LEVEL)
    {
        return(c('gamma',gamma.shape,gamma.rate))
    }

    # negative binomial
    res <- fitdistr(x, 'negative binomial')
    nbinom.size <- as.real(res$estimate[1])
    nbinom.mu <- as.real(res$estimate[2])
    y.nbinom <- rnbinom(length(x),size=nbinom.size,mu=nbinom.mu)
    res.ks.nbinom <- ks.boot(x,y.nbinom)
    res.chisq.nbinom.pval <- rw_chisq(x,y.nbinom)
    if (res.ks.nbinom$ks.boot.pvalue > SIGN.LEVEL && res.chisq.nbinom.pval > SIGN.LEVEL)
    {
        return(c('nbinom',nbinom.size,nbinom.mu))
    }
    

    # geometric
    res <- fitdistr(x, 'geometric')
    geom.prob <- as.real(res$estimate[1])
    y.geom <- rgeom(length(x),prob=geom.prob)
    res.ks.geom <- ks.boot(x,y.geom)
    res.chisq.geom.pval <- rw_chisq(x,y.geom)
    if (res.ks.geom$ks.boot.pvalue > SIGN.LEVEL && res.chisq.geom.pval > SIGN.LEVEl)
    {
        return(c('geom',geom.prob))
    }
 
    # normal
    res <- fitdistr(x, 'normal')
    norm.mean <- as.real(res$estimate[1])
    norm.sd <- as.real(res$estimate[2])
    y.norm <- rnorm(length(x),mean=norm.mean,sd=norm.sd)
    res.ks.norm <- ks.boot(x,y.norm)
    res.chisq.norm.pval <- rw_chisq(x,y.norm)
    if (res.ks.norm.$ks.boot.pvalue > SIGN.LEVEL && res.chisq.norm.pval > SIGN.LEVEL)
    {
        return(c('norm',norm.mean,norm.sd))
    }

    # log-normal
    res <- fitdistr(x, 'log-normal')
    lnorm.meanlog <- as.real(res$estimate[1])
    lnorm.sdlog <- as.real(res$estimate[2])
    y.lnorm <- rlnorm(length(x),meanlog=lnorm.meanlog,sdlog=lnorm.sdlog)
    res.ks.lnorm <- ks.boot(x,y.lnorm) 
    res.chisq.lnorm.pval <- rw_chisq(x,y.lnorm)
    if (res.ks.lnorm$ks.boot.pvalue > SIGN.LEVEL && res.chisq.lnorm.pval > SIGN.LEVEL)
    {
        return(c('lnorm',lnorm.meanlog,lnorm.sdlog))
    }

    # logistic
    res <- fitdistr(x, 'logistic')
    logis.location <- as.real(res$estimate[1])
    logis.scale <- as.real(res$estimate[2])
    y.logis <- rlogis(length(x),location=logis.location,scale=logis.scale)
    res.ks.logis <- ks.boot(x,y.logis)
    res.chisq.logis.pval <- rw_chisq(x,y.logis)
    if (res.ks.logis$ks.boot.pvalue > SIGN.LEVEL && res.chisq.logis.pval > SIGN.LEVEL)
    {
        return(c('logis',logis.location,logis.scale))
    }

    # exponential
    res <- fitdistr(x, 'exponential')
    exp.rate <- as.real(res$estimate[1])
    y.exp <- rexp(length(x),rate=exp.rate)
    res.ks.exp <- ks.boot(x,y.exp)
    res.chisq.exp.pval <- rw_chisq(x,y.exp) 
    if (res.ks.exp$ks.boot.pvalue > SIGN.LEVEL && res.chisq.exp.pval > SIGN.LEVEL)
    {
        return(c('exp',exp.rate))
    }

    # cauchy
    res <- fitdistr(x, 'cauchy')
    cauchy.location <- as.real(res$estimate[1])
    cauchy.scale <- as.real(res$estimate[2])
    y.cauchy <- rcauchy(length(x),location=cauchy.location,scale=cauchy.scale)
    res.ks.cauchy <- ks.boot(x,y.cauchy)
    res.chisq.cauchy.pval <- rw_chisq(x,y.cauchy)
    if (res.ks.cauchy$ks.boot.pvalue > SIGN.LEVEL && res.chisq.cauchy.pval > SIGN.LEVEL)
    {
        return(c('cauchy',cauchy.location,cauchy.scale))
    }

    # Poisson
    res <- fitdistr(x, 'Poisson')
    pois.lambda <- as.real(res$estimate[1])
    y.pois <- rpois(length(x),lambda=pois.lambda)
    res.ks.pois <- ks.boot(x,y.pois)
    res.chisq.pois.pval <- rw_chisq(x,y.pois)
    if (res.ks.pois$ks.boot.pvalue > SIGN.LEVEL && res.chisq.pois.pval > SIGN.LEVEL)
    {
        return(c('pois',pois.lambda))
    }

    # weibull
    res <- fitdistr(x, 'weibull')
    weibull.shape <- as.real(res$estimate[1])
    weibull.scale <- as.real(res$estimate[2])
    y.weibull <- rweibull(length(x),shape=weibull.shape,scale=weibull.scale)
    res.ks.weibull <- ks.boot(x,y.weibull)
    res.chisq.weibull.pval <- rw_chisq(x,y.weibull)
    if (res.ks.weibull$ks.boot.pvalue > SIGN.LEVEL && res.chisq.weibull.pval > SIGN.LEVEL)
    {
        return(c('weibull',weibull.shape,weibull.scale))
    }

    return(c())

}


rw_chisq <- function(x,y)
{
    breaks <- hist(x,plot=FALSE)$breaks

    x.cut <- cut(x, breaks = breaks)
    x.cut.tbl <- table(x.cut)

    y.cut <- cut(y, breaks = breaks)
    y.cut.tbl <- table(y.cut)

    res <- chisq.test(x.cut,y.cut)
    pval <- res$p.value

    return(pval)
}




