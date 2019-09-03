; memq doc
; https://www.gnu.org/software/mit-scheme/documentation/mit-scheme-ref/Searching-Lists.html#Searching-Lists
(define (count-pairs x)
  (define (iter x mem-list)
    (if (and (pair? x)
             (false? (memq x mem-list)))
        (iter (car x)
              (iter (cdr x)
                    (cons x mem-list)))
        mem-list))
  (length (iter x '())))
