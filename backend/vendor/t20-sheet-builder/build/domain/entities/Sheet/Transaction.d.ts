import { type Action } from '../Action/Action';
import type { SheetInterface } from './SheetInterface';
export declare class Transaction<S extends SheetInterface = SheetInterface> {
    readonly sheet: S;
    private readonly actionsQueue;
    constructor(sheet: S);
    run(action: Action): void;
    commit(): void;
}
