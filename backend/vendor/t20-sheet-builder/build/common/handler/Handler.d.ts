export declare abstract class Handler<Request, Return> {
    protected nextHandler: Handler<Request, Return> | undefined;
    setNext(handler: Handler<Request, Return>): Handler<Request, Return>;
    execute(request: Request): Return;
    protected abstract handle(request: Request): Return;
    protected abstract shouldHandle(request: Request): boolean;
}
