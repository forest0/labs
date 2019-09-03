(define (make-frame-v1 origin edge1 edge2)
  (list origin edge1 edge2))

(define (origin-frame-v1 frame)
  (car frame))

(define (edge1-frame-v1 frame)
  (cadr frame))

(define (edge2-frame-v1 frame)
  (caddr frame))


(define (make-frame-v2 origin edge1 edge2)
  (cons origin (cons edge1 edge2)))

(define (origin-frame-v2 frame)
  (car frame))

(define (edge1-frame-v2 frame)
  (cadr frame))

(define (edge2-frame-v2 frame)
  (cddr frame))
