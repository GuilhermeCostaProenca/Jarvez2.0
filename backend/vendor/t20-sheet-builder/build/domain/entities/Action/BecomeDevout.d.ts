import { Action, type ActionSubClassParams } from './Action';
export declare class BecomeDevout extends Action<'becomeDevout'> {
    constructor(params: ActionSubClassParams<'becomeDevout'>);
    execute(): void;
    getDescription(): string;
}
