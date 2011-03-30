
plot_specificity_list <- function(posnames)
{

  plotwidth <- 7
  plotheight <- 3
  pointsize <- 12

  pdf("tolerance_boxplot.pdf", width=plotwidth, height=plotheight, pointsize=pointsize)
  pdfdev <- dev.cur()
  png("tolerance_boxplot.png", width=plotwidth*72, height=plotheight*72*length(posnames), pointsize=3/2*pointsize)
  pngdev <- dev.cur()
  par(mfrow=c(length(posnames), 1))

  aa_labels <- c("W","F","Y","M","L","I","V","A","G","S","T","R","K","H","N","Q","D","E","P")

  pwms <- matrix(0,19,0)
  dimnames(pwms) <- list(c("W","F","Y","M","L","I","V","A","G","S","T","R","K","H","N","Q","D","E","P"))

  for (i in seq_along(posnames)) {

    fn_in <- paste("freq_", posnames[i],".txt", sep="")
    table_backrub <- read.table(fn_in)
    trans_table <- t(as.matrix(table_backrub))
    trans_table <- apply(trans_table,c(1,2),function(x) { x/100 })
    # print(trans_table)
    # print(dim(trans_table)[1])
    pwm <- apply(trans_table, 2, function(x) sum(x)/dim(trans_table)[1]) # sum lines up and divides them
    pwm <- as.matrix(pwm)
    colnames(pwm) <- list(posnames[i])
    # print(pwm)
    pwms <- cbind(pwms,pwm)
    # print(pwms)
    # print(apply(pwms,2,sum))

    mp <- aa_labels #c(1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19)
    colnames(trans_table) <- mp
    rownames(trans_table) <- NULL

    y_lim <- 0.6
    if (max(trans_table) > y_lim) y_lim <- max(trans_table) + 0.1

    trans_table <- data.frame(Residue=factor(rep(colnames(trans_table), each = nrow(trans_table)), colnames(trans_table)),Frequency = as.vector(trans_table))

    for (type in c("pdf", "png", "pngsep")) {

      if (type == "pdf") dev.set(pdfdev)
      if (type == "png") dev.set(pngdev)
      if (type == "pngsep") png(paste("tolerance_boxplot_", posnames[i],".png", sep=""), width=plotwidth*72, height=plotheight*72, pointsize=pointsize)

      par(mar = c(2.8, 2.8, 1.5, 0.1), mgp = c(1.7, y_lim, 0))
      main <- paste("Residue", posnames[i], "Sequence Tolerance Boxplot")
      plot(0, 0, type="n", xlim=c(1,20), ylim=c(0,y_lim), main=main, xlab="Amino Acid", ylab="Predicted Frequency", axes=FALSE)
      abline(a=0.1,b=0, col="red")
      abline(h=seq(0, 1, by=.2), col="gray")
      boxplot(Frequency ~ Residue, data=trans_table, col="white", add=TRUE)
      # boxplot(Percentage ~ Residue, data=trans_table, axes=FALSE,  at=mp, outline=FALSE, col="blue",lwd=2,border=TRUE,ylim=c(0,60),xlim=c(0.5,19.5),ylab="",xlab="",main=design_res,cex.main=2.3)
      if (type == "pngsep") dev.off()
    }
  }
  dev.off(pdfdev)
  dev.off(pngdev)

  write.table(pwms, "tolerance_pwm.txt", quote=FALSE, sep="\t", col.names=NA)

}

# example uses:
# plot_specificity("freq_A65.txt", "A65", "plot_A65.png")
# plot_specificity_list(c('A65','B3','B4','B5','B6'))




