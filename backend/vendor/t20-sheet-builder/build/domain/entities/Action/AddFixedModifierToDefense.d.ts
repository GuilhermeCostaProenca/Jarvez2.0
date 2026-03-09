import { Action, type ActionSubClassParams } from './Action';
export declare class AddFixedModifierToDefense extends Action<'addFixedModifierToDefense'> {
    constructor(params: ActionSubClassParams<'addFixedModifierToDefense'>);
    execute(): void;
    getDescription(): string;
}
