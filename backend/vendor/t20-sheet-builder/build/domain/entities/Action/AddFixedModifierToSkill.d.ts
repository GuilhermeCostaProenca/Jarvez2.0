import { Action, type ActionSubClassParams } from './Action';
export declare class AddFixedModifierToSkill extends Action<'addFixedModifierToSkill'> {
    constructor(params: ActionSubClassParams<'addFixedModifierToSkill'>);
    execute(): void;
    getDescription(): string;
}
