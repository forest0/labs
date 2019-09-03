(define (make-queue)
  (let ((front-ptr '())
        (rear-ptr '()))

    (define (empty-queue?)
      (null? front-ptr))
    (define (insert-queue! item)
      (let ((new (list item)))
        (cond ((empty-queue?)
               (set! front-ptr new)
               (set! rear-ptr new)
               front-ptr)
              (else
                (set-cdr! rear-ptr new)
                (set! rear-ptr new)
                front-ptr))))
    (define (delete-queue!)
      (cond ((empty-queue?)
             (error "DELETE! called with an empty queue"))
            (else
              (set! front-ptr (cdr front-ptr))
              front-ptr)))
    (define (front-queue)
      (if (empty-queue?)
          (error "FRONT-QUEUE called with an empty queue")
          (car front-ptr)))
    (define (dispatch m)
      (cond ((eq? m 'empty-queue?) empty-queue?)
            ((eq? m 'insert-queue!) insert-queue!)
            ((eq? m 'delete-queue!) delete-queue!)
            ((eq? m 'front-queue) front-queue)
            (else
              (error "Unknown operation -- DISPATCH" m))))
    dispatch))
