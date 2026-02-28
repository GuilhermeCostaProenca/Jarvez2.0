import { Action, type ActionSubClassParams } from './Action';
export declare class DecreaseAttribute extends Action<'decreaseAttribute'> {
    constructor(params: ActionSubClassParams<'decreaseAttribute'>);
    execute(): void;
    getDescription(): string;
}
