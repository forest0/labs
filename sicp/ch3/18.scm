(define (contains-cycle? x)
  (define (iter x mem-list)
    (cond ((null? x) #f)
          ((not (false? (memq (car x) mem-list))) #t)
          (else (iter (cdr x)
                      (cons (car x) mem-list)))))
  (iter x '()))