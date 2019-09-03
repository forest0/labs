; semantics
(define (unless condition usual-value exceptional-value)
  (if condition
      exceptional-value
      usual-value))

(define (unless->if expr)
  (define (unless-condition)
    (cadr expr))
  (define (unless-usual-value expr)
    (caddr expr))
  (define (unless-exceptional-value vars)
    (cadddr expr))

    (make-if (unless-condition expr)
             (unless-exceptional-value expr)
             (unless-usual-value expr))))
