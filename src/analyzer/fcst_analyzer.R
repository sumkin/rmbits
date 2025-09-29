#################################
#
#      SUMMARY STATISTICS
#
#################################

get_me <- function(l)
{
    ret <- mean(l)
    return(ret)
}

get_mae <- function(l)
{
    ret <- mean(abs(l))
    return(ret)
}

get_mse <- function(l)
{
    ret <- mean(l*l)
    return(ret)
}

get_sd <- function(l)
{
    ret <- sd(l)
    return(ret)
}


#################################
#
#      TREND ESTIMATION      
#
#################################

get_trend_pol2 <- function(l)
{
    t1 <- seq(1,length(l))
    t2 <- t1^2
    res <- lm(l ~ t1 + t2)
    res.sum <- summary(res)
    return (res.sum)
}


#################################
#
#      HYPOTHESIS TESTING
#
#################################

get_shapiro_wilk_p_value <- function(l)
{
    #qqplot(l,round(rnorm(length(l),mean=mean(l),sd=sd(l))),xlim=c(-10,10),ylim=c(-10,10))
    res <- shapiro.test(l)
    return(res$p.value)
}

get_ks_p_value <- function(l)
{
    mn <- mean(l)
    sd <- sd(l)
    res <- ks.boot(l,round(rnorm(length(l),mn,sd)))
    print(res)
    return(res$ks.boot.pvalue)
}

get_cr_von_mis_p_value <- function(l)
{
    mn <- mean(l)
    sd <- sd(l)
    
    lprime <- round(rnorm(length(l),mn,sd))
    print('lprime calculated')
    cvm <- cvmts.test(l,lprime)
    print('cvm calculated')
    pval <- cvmts.pval(cvm,length(l),length(l))
    print('pval calculated')  

    return(pval)
}

get_ljung_box_pval <- function(l)
{
    res <- Box.test(l, type='Ljung-Box')
    pval <- res$p.value

    return(pval)
}
























