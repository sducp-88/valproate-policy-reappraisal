Sys.setlocale('LC_ALL','C')
extra_lib <- Sys.getenv('VALPROATE_R_LIB', '')
if(nzchar(extra_lib)) .libPaths(c(extra_lib,.libPaths()))
suppressPackageStartupMessages(library(nlme))
suppressPackageStartupMessages(library(jsonlite))
args<-commandArgs(trailingOnly=TRUE)
root<-if(length(args)) args[1] else '.'
out<-file.path(root,'ANALYSIS','results')
d<-read.csv(file.path(root,'ANALYSIS','data','monthly_analysis.csv'))
d$month<-factor(d$month,levels=1:12)
d$sin12<-sin(2*pi*d$time/12);d$cos12<-cos(2*pi*d$time/12)
stopifnot(nrow(d)==40,all(d$time==0:39))
fits<-list(); curves<-list()
fit_one<-function(outcome,break_at=202311,season='month',id=NULL,ar_order=1){
 dd<-d;dd$y<-dd[[outcome]]
 start<-dd$time[dd$YEAR_MONTH==break_at];stopifnot(length(start)==1)
 dd$post<-as.integer(dd$time>=start);dd$after<-pmax(dd$time-start,0)
 form<-switch(season,month=y~time+post+after+month,harmonic=y~time+post+after+sin12+cos12,none=y~time+post+after)
 corr<-if(ar_order==1) corAR1(form=~time) else corARMA(p=ar_order,q=0,form=~time)
 f<-gls(form,data=dd,correlation=corr,method='REML',control=glsControl(msMaxIter=200))
 b<-coef(f);V<-vcov(f);df<-nrow(dd)-length(b);crit<-qt(.975,df)
 vec<-function(){setNames(rep(0,length(b)),names(b))}
 est<-function(L){z<-sum(L*b);se<-sqrt(drop(t(L)%*%V%*%L));list(estimate=z,se=se,lower=z-crit*se,upper=z+crit*se)}
 L<-vec();L['time']<-1;pre<-est(L)
 L<-vec();L['post']<-1;step<-est(L)
 L<-vec();L['after']<-1;change<-est(L)
 L['time']<-1;post_slope<-est(L)
 L<-vec();L['post']<-1;L['after']<-max(dd$after);delta<-est(L)
 X<-model.matrix(form,dd);C<-X;C[,c('post','after')]<-0
 counter<-drop(C%*%b);fitted<-drop(X%*%b)
 x<-C[nrow(C),];den<-sum(x*b);num<-sum(L*b)
 gradient<-L/den-num*x/den^2;se<-sqrt(drop(t(gradient)%*%V%*%gradient))*100
 pct<-100*num/den
 e<-as.numeric(residuals(f,type='normalized'))
 if(is.null(id)) id<-paste(outcome,break_at,season,sep='_')
 tt<-data.frame(id=id,year_month=dd$YEAR_MONTH,observed=dd$y,fitted=fitted,counterfactual=counter,
  fitted_se=sqrt(rowSums((X%*%V)*X)),counterfactual_se=sqrt(rowSums((C%*%V)*C)),normalized_residual=e)
 curves[[id]]<<-tt
 info<-list(id=id,outcome=outcome,break_at=break_at,season=season,observations=40,parameters=length(b),residual_df=df,
  ar_order=ar_order,rho=as.numeric(coef(f$modelStruct$corStruct,unconstrained=FALSE))[1],ar_coefficients=as.numeric(coef(f$modelStruct$corStruct,unconstrained=FALSE)),pre_slope=pre,immediate_level=step,slope_change=change,post_slope=post_slope,
  terminal_difference=delta,terminal_counterfactual=den,terminal_fitted=tail(fitted,1),
  terminal_percent=list(estimate=pct,se=se,lower=pct-crit*se,upper=pct+crit*se),
  normalized_acf=as.numeric(acf(e,lag.max=12,plot=FALSE)$acf),coefficients=as.list(b),covariance=unname(V),coefficient_order=names(b))
 fits[[id]]<<-info;invisible(info)
}
for(y in c('daily_ddd','items','rows','unweighted_daily','ddd_30_4')) fit_one(y)
for(y in c('daily_items','daily_rows','sodium_only','solid_only')) fit_one(y)
for(br in c(202310,202312,202402)) fit_one('daily_ddd',br)
fit_one('daily_ddd',season='harmonic');fit_one('daily_ddd',season='none')
fit_one('daily_ddd',id='daily_ddd_202311_month_ar2',ar_order=2)
write_json(list(date='2026-11-02',primary='daily_ddd_202311_month',method='REML AR(1) generalized least squares; t intervals and delta-method relative contrast, conditional on fitted correlation',fits=fits),file.path(out,'models.json'),auto_unbox=TRUE,pretty=TRUE,digits=14)
write.csv(do.call(rbind,curves),file.path(out,'model_curves.csv'),row.names=FALSE)
flat<-do.call(rbind,lapply(fits,function(x)data.frame(id=x$id,estimate=x$terminal_percent$estimate,lower=x$terminal_percent$lower,upper=x$terminal_percent$upper,level=x$immediate_level$estimate,post_slope=x$post_slope$estimate,rho=x$rho,df=x$residual_df)))
write.csv(flat,file.path(out,'model_summary.csv'),row.names=FALSE)
writeLines(capture.output(sessionInfo()),file.path(out,'R_sessionInfo.txt'))
print(flat,row.names=FALSE)
