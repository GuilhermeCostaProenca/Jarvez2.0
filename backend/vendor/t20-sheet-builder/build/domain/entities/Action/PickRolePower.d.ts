import { Action, type ActionSubClassParams } from './Action';
export declare class PickRolePower extends Action<'pickRolePower'> {
    constructor(params: ActionSubClassParams<'pickRolePower'>);
    execute(): void;
    getDescription(): string;
}
