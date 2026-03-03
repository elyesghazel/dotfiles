function npr
    echo "Select project category:"
    echo "1) Swisscom"
    echo "2) Business / Private"
    echo "3) Education / School"
    read -l choice

    set -l base_path ""
    switch $choice
        case 1
            set base_path $HOME/projects/01_swisscom
        case 2
            set base_path $BIZ_PATH
        case 3
            set base_path $EDU_PATH
        case '*'
            echo "Error: Invalid selection."
            return 1
    end

    echo "Enter project name:"
    read -l project_name

    if test -z "$project_name"
        echo "Error: Project name cannot be empty."
        return 1
    end

    set -l final_path "$base_path/$project_name"

    mkdir -p $final_path
    cd $final_path
    git init -b main
    echo "# $project_name" > README.md
    
    echo "Status: Project initialized at $final_path"
    code .
end