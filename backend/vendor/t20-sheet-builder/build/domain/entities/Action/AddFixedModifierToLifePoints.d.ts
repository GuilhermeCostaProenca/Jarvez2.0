import { Action, type ActionSubClassParams } from './Action';
export declare class AddFixedModifierToLifePoints extends Action<'addFixedModifierToLifePoints'> {
    constructor(params: ActionSubClassParams<'addFixedModifierToLifePoints'>);
    execute(): void;
    getDescription(): string;
}
