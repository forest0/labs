(load "time.scm")

(define (make-logger . name)
  (let ((log-levels (list (cons 'SILENCE 0)
                          (cons 'DEBUG 1)
                          (cons 'INFO 2)
                          (cons 'WARNING 3)
                          (cons 'ERROR 4)))
        (log-level 1))
    ; (define (set-level! level)
    ;   ())
    (define (level->number level)
      (cond ((eq? level 'SILENCE) 0)
            ((eq? level 'DEBUG) 1)
            ((eq? level 'INFO) 2)
            ((eq? level 'WARNING) 3)
            ((eq? level 'ERROR) 4)
            (else (error "undefined log level --" level))))
    (define (number->level number)
      (cond ((eq? number 0) 'SILENCE)
            ((eq? number 1) 'DEBUG)
            ((eq? number 2) 'INFO)
            ((eq? number 3) 'WARNING)
            ((eq? number 4) 'ERROR)
            (else (error "undefined log level number --" number))))
    (define (do-log level msg)
      ; not efficient
      (define (string-append* string-list)
        (define (iter remain result)
          (if (null? remain)
              result
              (iter (cdr remain) (string-append result
                                                (string (car remain))))))
        (iter msg ""))
      (newline)
      (display (time->string))
      (display " [")
      (display (string-upcase (symbol->string level)))
      (display "] ")
      (display (string-append* msg)))

    (define (dispatch level . msg)
      (if (>= (level->number level) log-level)
          (do-log level msg)))
    dispatch))
