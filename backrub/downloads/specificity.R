# Define vectors for mapping between 1 and 3 character residue names

aa3 <- c("TRP", "PHE", "TYR", "MET", "LEU", "ILE", "VAL", "ALA", "GLY", "SER", 
         "THR", "ARG", "LYS", "HIS", "ASN", "GLN", "ASP", "GLU", "PRO", "CYS")

aa1 <- c("W", "F", "Y", "M", "L", "I", "V", "A", "G", "S", 
         "T", "R", "K", "H", "N", "Q", "D", "E", "P", "C")

names(aa3) <- aa1
names(aa1) <- aa3

# This function reads *.ga.entities checkpoint files. It assumes that all 
# entities have the same composition. It reads checkpointed Entity and 
# MultiStateEntity objects. It returns a data.frame object with a row for each 
# entity. The traits at each sequence position are given first, then the 
# overall fitness, then the state fitnesses and metric values.

read_ga_entities <- function(filename, restypes = NULL) {

	metric_types <- list(Real = numeric(), Int = integer(), Size = integer(), Bool = logical())
	
	file_con <- if (length(grep("\\.gz$", filename))) gzfile(filename) else file(filename)
	tokens <- scan(file_con, character(), 300, quiet = TRUE)
	close(file_con)
	
	if (tokens[1] != "traits") stop(paste(filename, "does not appear to be an entities file"))
	
	scan_what <- list(NULL)
	
	# set up the traits input
	num_traits <- grep("fitness", tokens)[1]-2
	res_nums <- lapply(strsplit(tokens[seq_len(num_traits)+1], "\\."), "[[", 1)
	traits_what <- rep(list(character()), num_traits)
	names(traits_what) <- paste("pos", res_nums, sep = "")
	
	scan_what <- c(scan_what, traits_what, list(NULL, fitness = numeric()))
	
	# handle additional MultiStateEntity data
	if (tokens[num_traits+4] == "states") {
	
		scan_what <- c(scan_what, list(NULL, NULL))
		
		# iterate over the number of states
		num_states <- as.integer(tokens[num_traits+5])
		token_offset <- num_traits+6
		for (i in seq_len(num_states)) {
			state_what <- list(NULL, numeric(), NULL, NULL)
			names(state_what) <- c("", paste("state", i, "_fitness", sep = ""), "", "")
			scan_what <- c(scan_what, state_what)
			
			# iterate over the number of metrics
			num_metrics <- as.integer(tokens[token_offset+3])
			token_offset <- token_offset+4
			for (j in seq_len(num_metrics)) {
			
				metric_name <- paste("state", i, "_", tokens[token_offset], sep = "")
				metric_type <- tokens[token_offset+1]
				
				scan_what <- c(scan_what, list(NULL, NULL))
				token_offset <- token_offset + 2
				
				if (length(grep("\\[$", metric_type))) {
					# handle vector metrics
					metric_length <- which(tokens[-seq_len(token_offset-1)] == "]")[1] - 1
					metric_type <- substr(metric_type, 1, nchar(metric_type)-1)
					metric_what <- rep(list(metric_types[[metric_type]]), metric_length)
					names(metric_what) <- paste(metric_name, seq_len(metric_length), sep = "")
					scan_what <- c(scan_what, metric_what, list(NULL))
					token_offset <- token_offset + metric_length + 1
				} else {
					# handle scalar metrics
					metric_what <- list(metric_types[[metric_type]])
					names(metric_what) <- metric_name
					scan_what <- c(scan_what, metric_what)
					token_offset <- token_offset + 1
				}
			}
		}
	}
	
	file_con <- if (length(grep("\\.gz$", filename))) gzfile(filename) else file(filename)
	result <- scan(file_con, scan_what, quiet = TRUE)[names(scan_what) != ""]
	close(file_con)
	
	if (is.null(restypes)) {
		for (i in seq_len(num_traits)) {
			result[[i]] <- sub(".+\\.", "", result[[i]])
		}
	} else {
		for (i in seq_len(num_traits)) {
			result[[i]] <- factor(sub(".+\\.", "", result[[i]]), restypes)
		}
	}
	
	as.data.frame(result)
}

# Read a list of *.ga.entities checkpoint files out of a directory. By default,
# the parsed data is saved in the R format

read_ga_entities_list <- function(dirpath, filepattern = NULL, recompute = FALSE, savedata = TRUE) {

	filename <- file.path(dirpath, paste("entities", filepattern, ".Rda", sep = ""))
	
	if (file.exists(filename) && !recompute) {
		load(filename)
	} else {
		simpattern <- if (is.null(filepattern)) "" else filepattern
		
		entitiesfiles <- list.files(dirpath, pattern = paste(simpattern, ".*\\.ga\\.entities", sep = ""),
		                            full.names = TRUE, recursive = TRUE)
		entitiesfiles <- entitiesfiles[file.info(entitiesfiles)$size > 0]
		
		entitieslist <- vector("list", length(entitiesfiles))
		
		for (i in seq(along = entitiesfiles)) {
			print(entitiesfiles[i])
			entitieslist[[i]] <- read_ga_entities(entitiesfiles[i], unname(aa3))
		}
		
		if (savedata == TRUE) save(entitieslist, file = filename)
	}
	
	entitieslist
}

# This function returns the fitness of a given set of entities

entities_fitness <- function(entities, fitness_coef = NULL) {

	if (is.null(fitness_coef)) {
		fitness_coef <- c(fitness = 1)
	}
	
	fitness_matrix <- as.matrix(entities[,names(fitness_coef),drop=FALSE])
	
	fitness_matrix %*% fitness_coef
}

# This function takes an entities data frame as read by read_ga_entities and 
# determines a profile weight matrix for the sampled sequence positions. It 
# uses either a fitness cutoff above the sequence with the best fitness, or
# Boltzmann weighting of the those energies. The total fitness is calculated
# by weighting numeric data read along with the sequences.
# WARNING: This function assumes the levels of all factors are identical!

entities_pwm <- function(entities, thresh_or_temp, fitness_coef = NULL, 
                         type = c("cutoff", "boltzmann")) {

	type <- match.arg(type)
	
	fitness <- entities_fitness(entities, fitness_coef)
	if (type == "cutoff") {
		weight <- fitness <= min(fitness)+thresh_or_temp
	} else {
		if (thresh_or_temp != 0) {
			weight <- exp(-fitness/thresh_or_temp)
		} else {
			weight <- fitness == min(fitness)
		}
	}
	
	pos_columns <- grep("^pos", colnames(entities))
	freqmat <- matrix(nrow = length(levels(entities[,1])), ncol = length(pos_columns))
	
	weight_sum <- sum(weight)
	for (i in seq_along(pos_columns)) {
		freqmat[,i] <- tapply(weight, entities[,pos_columns[i]], sum)/weight_sum
		freqmat[is.na(freqmat[,i]),i] <- 0
	}
	rownames(freqmat) <- levels(entities[,1])
	
	#print(freqmat)
	
	freqmat
}

# This function takes a list of entities data frames and returns a list of
# profile weight matrices, where each matrix correspons to a single sequence
# position. The matrices will have one column for every input data frame.
# WARNING: This function assumes the levels of all factors are identical!

entities_pwms <- function(entitieslist, thresh_or_temp, fitness_coef = NULL, 
                          type = c("cutoff", "boltzmann")) {

	type <- match.arg(type)
	naa <- length(levels(entitieslist[[1]][,1]))
	
	pwmlist <- rep(list(matrix(nrow = naa, ncol = 0)), length(grep("^pos", colnames(entitieslist[[1]]))))
	
	for (i in seq(along = entitieslist) ){
	
		freqmat <- entities_pwm(entitieslist[[i]], thresh_or_temp, fitness_coef, type)
		
		for (j in seq(along = pwmlist)) {
		
			pwmlist[[j]] <- cbind(pwmlist[[j]], freqmat[,j])
		}
	}
	
	#print(pwmlist)
	
	pwmlist
}

# This function extracts the sequence from a PDB file. The residue IDs
# (<chainID><resSeq><iCode>) are given in as the names.

pdb_sequence <- function(pdbpath) {

	pdblines <- readLines(pdbpath)
	atomlines <- grep("^ATOM", pdblines, value=TRUE)
	resName <- substr(atomlines, 18, 20)
	resID <- substr(atomlines, 22, 27)
	
	resID <- gsub("^ ", "_", resID)
	resID <- gsub(" ", "", resID)
	
	names(resName) <- resID
	
	resName[!duplicated(resID)]
}

# The function converts a profile weight matrix to a matrix of sequences with 
# the same approximate distribution as the original PWM. 

pwm_to_seqmat <- function(pwm, numseq=100) {


	seqmat <- matrix(character(), nrow=numseq, ncol=ncol(pwm))
	for (i in seq_len(ncol(pwm))) {
		colfun <- stepfun(c(0,cumsum(pwm[,i])), c(1,seq_along(pwm[,i]),length(pwm[,i])))
		funx <- seq(0, 1, length.out=numseq+1)
		funx <- funx[-1] - mean(diff(funx))/2
		seqmat[,i] <- names(pwm[,i])[colfun(funx)]
	}
	
	colnames(seqmat) <- colnames(pwm)

	seqmat
}

# This function is the main data processing procedure. It takes a directory 
# path which contains *.ga.entities files. It reads all those files and
# produces a set of boxplots in several different file formats. It also 
# generates a profile weight matrix and FASTA file for producing a sequence 
# logo.

process_specificity <- function(dirpath, fitness_coef = c(1, 1, 1, 2),
                                thresh_or_temp = 3, 
                                type = c("cutoff", "boltzmann"),
                                percentile = .5) {

	type <- match.arg(type)
	names(fitness_coef) <- c("state1_fitness_comp1", "state1_fitness_comp2",
	                         "state1_fitness_comp3", "state1_fitness_comp4")
	
	entities <- read_ga_entities_list(dirpath)
	pwms <- entities_pwms(entities, thresh_or_temp, fitness_coef, type)
	
	posnames <- colnames(entities[[1]])[seq_along(pwms)]
	posnames <- gsub("pos", "", posnames)
	
	backruboutput <- file.path(dirpath, "backrub_0_stdout.txt")
	if (file.exists(backruboutput)) {
		backrubcmd <- readLines(backruboutput, 1)
		startpdbfile <- gsub("^.+ -s ([^ ]+) .+$", "\\1", backrubcmd)
		pdbseq <- pdb_sequence(file.path(dirpath, startpdbfile))
		posnames <- names(pdbseq)[as.integer(posnames)]
	}
	
	pwmsdimnames <- list(aa=aa1[rownames(pwms[[1]])], rep=NULL, pos=posnames)
	
	pwms <- array(do.call("c", pwms), dim = c(dim(pwms[[1]]), length(pwms)))
	dimnames(pwms) <- pwmsdimnames
	
	pwm <- apply(pwms, c(1,3), quantile, percentile)
	
	minnotzero <- function(x) {
		x <- x[x!=0]
		if (length(x)) return(min(x))
		NA
	}
	plastmin <- apply(pwms, c(1,3), minnotzero)
	correcteddist <- apply(plastmin, 2, function(x) as.numeric(!is.na(x) & x==min(x, na.rm = TRUE)))
	
	for (i in which(colSums(pwm) == 0)) {
		#print(paste("Correcting", i))
		pwm[,i] <- correcteddist[,i]
	}
	
	pwm <- apply(pwm, 2, function(x) x/sum(x))
	
	write.table(pwm, "specificity_pwm.txt", quote=FALSE, sep="\t", col.names=NA)
	
	seqmat <- pwm_to_seqmat(pwm)
	
	cat(paste(">", seq_len(nrow(seqmat)), "\n", apply(seqmat, 1, paste, collapse=""), sep=""), file="specificity_sequences.fasta", sep="\n")
	
	plotwidth <- 7
	plotheight <- 3
	pointsize <- 12
	
	pdf("specificity_boxplot.pdf", width=plotwidth, height=plotheight, pointsize=pointsize)
	pdfdev <- dev.cur()
	png("specificity_boxplot.png", width=plotwidth*72, height=plotheight*72*length(posnames), pointsize=3/2*pointsize)
	pngdev <- dev.cur()
	par(mfrow=c(length(posnames), 1))
	
	for (i in seq_along(posnames)) {
		
		for (type in c("pdf", "png", "pngsep")) {
			
			if (type == "pdf") dev.set(pdfdev)
			if (type == "png") dev.set(pngdev)
			if (type == "pngsep") png(paste("specificity_boxplot_", posnames[i],".png", sep=""), width=plotwidth*72, height=plotheight*72, pointsize=pointsize)
			
			par(mar = c(2.8, 2.8, 1.5, 0.1), mgp = c(1.7, 0.6, 0))
			main <- paste("Residue", posnames[i], "Specificity Boxplot")
			plot(0, 0, type="n", xlim=c(1,20), ylim=c(0,1), main=main, xlab="Amino Acid", ylab="Predicted Frequency", axes=FALSE)
			abline(h=seq(0, 1, by=.2), col="gray")
			boxplot(t(pwms[,,i]), col="white", add=TRUE)
			points(1:20, pwm[,i], pch=4, col="blue")
			
			if (type == "pngsep") dev.off()
		}
	}
	dev.off(pdfdev)
	dev.off(pngdev)
}
