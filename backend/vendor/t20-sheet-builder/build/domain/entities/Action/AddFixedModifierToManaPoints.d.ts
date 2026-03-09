import { Action, type ActionSubClassParams } from './Action';
export declare class AddFixedModifierToManaPoints extends Action<'addFixedModifierToManaPoints'> {
    constructor(params: ActionSubClassParams<'addFixedModifierToManaPoints'>);
    execute(): void;
    getDescription(): string;
}
