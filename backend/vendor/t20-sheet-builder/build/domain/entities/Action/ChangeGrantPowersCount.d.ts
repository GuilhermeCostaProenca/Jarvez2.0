import { Action, type ActionSubClassParams } from './Action';
export declare class ChangeGrantPowersCount extends Action<'changeGrantPowersCount'> {
    constructor(params: ActionSubClassParams<'changeGrantPowersCount'>);
    execute(): void;
    getDescription(): string;
}
