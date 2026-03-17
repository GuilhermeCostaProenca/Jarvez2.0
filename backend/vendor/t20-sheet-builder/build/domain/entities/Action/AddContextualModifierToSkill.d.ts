import { Action, type ActionSubClassParams } from './Action';
export declare class AddContextualModifierToSkill extends Action<'addContextualModifierToSkill'> {
    constructor(params: ActionSubClassParams<'addContextualModifierToSkill'>);
    execute(): void;
    getDescription(): string;
}
